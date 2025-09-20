# OceanBase 日语分词器接入指南

## 1. Docker 加速

首先配置 Docker 加速镜像，以提高镜像下载速度：

```bash
cat > /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://registry.cn-hangzhou.aliyuncs.com",
    "https://hub.icert.top",
    "https://ghcr.geekery.cn",
    "https://docker.1panel.live"
  ]
}
EOF
systemctl restart docker
```

## 2. 修改代码 - 向量库支持分词器配置

首先 clone 代码：
```bash
git clone git@github.com:langgenius/dify.git
```

### 2.1 修改配置文件

在 `api/configs/middleware/vdb/oceanbase_config.py` 最后追加如下行：

```python
    OCEANBASE_FULLTEXT_PARSER: str | None = Field(
        description="Fulltext parser to use for text indexing. Options: 'japanese_ftparser'(Japanese),'thai_ftparser' (Thai), 'ik' (Chinese), "
        "Default is 'ik'",
        default="ik",
    )
```

### 2.2 修改向量库实现

修改 `api/core/rag/datasource/vdb/oceanbase/oceanbase_vector.py:120-135` ,替换为以下内容：

```python
            logger.debug(f"DEBUG: Table '{self._collection_name}' created successfully")
            
            if self._hybrid_search_enabled:
                # Get parser from config or use default ik parser
                parser_name = dify_config.OCEANBASE_FULLTEXT_PARSER or "ik"
                logger.debug(f"DEBUG: Hybrid search is enabled, parser_name='{parser_name}'")
                    
                logger.debug(f"DEBUG: About to create fulltext index for collection '{self._collection_name}' using parser '{parser_name}'")
                    
                try:
                    sql_command = f"""ALTER TABLE {self._collection_name}
                    ADD FULLTEXT INDEX fulltext_index_for_col_text (text) WITH PARSER {parser_name}"""
                    logger.debug(f"DEBUG: Executing SQL: {sql_command}")
                    self._client.perform_raw_text_sql(sql_command)
                    logger.debug(f"DEBUG: Fulltext index created successfully for '{self._collection_name}'")
                except Exception as e:
                    logger.error(f"DEBUG: Exception occurred while creating fulltext index: {str(e)}")
                    logger.error(f"DEBUG: Exception type: {type(e)}")
                    raise Exception(
                        "Failed to add fulltext index to the target table, your OceanBase version must be 4.3.5.1 or above "
                        + "to support fulltext index and vector index in the same table",
                        e,
                    )
            else:
                logger.debug(f"DEBUG: Hybrid search is NOT enabled for '{self._collection_name}'")
```

### 2.3 修改 Docker Compose 配置

在 `docker/docker-compose.yaml:308` 上增加分词器配置：

```yaml
  OCEANBASE_FULLTEXT_PARSER: ${OCEANBASE_FULLTEXT_PARSER:-ik}
```

将 api、worker、worker_beat 的启动方式从使用 image 改成本地 build：

```yaml
    build:
      context: ../api
      dockerfile: Dockerfile
```

在 `docker/docker-compose.yaml:1101` 后追加语言编码配置：

```yaml
LANG: en_US.UTF-8
```

### 2.4 修改 Dockerfile 添加镜像源

修改 `api/Dockerfile`：

```dockerfile
# base image
FROM python:3.12-slim-bookworm AS base

WORKDIR /app/api

# Install uv
ENV UV_VERSION=0.8.9

RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple uv==${UV_VERSION}


FROM base AS packages

# if you located in China, you can use aliyun mirror to speed up
RUN sed -i 's@deb.debian.org@mirrors.aliyun.com@g' /etc/apt/sources.list.d/debian.sources

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc g++ libc-dev libffi-dev libgmp-dev libmpfr-dev libmpc-dev

# Install Python dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# production stage
FROM base AS production

ENV FLASK_APP=app.py
ENV EDITION=SELF_HOSTED
ENV DEPLOY_ENV=PRODUCTION
ENV CONSOLE_API_URL=http://127.0.0.1:5001
ENV CONSOLE_WEB_URL=http://127.0.0.1:3000
ENV SERVICE_API_URL=http://127.0.0.1:5001
ENV APP_WEB_URL=http://127.0.0.1:3000

EXPOSE 5001

# set timezone
ENV TZ=UTC

# Set UTF-8 locale
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV PYTHONIOENCODING=utf-8

WORKDIR /app/api

RUN sed -i 's@deb.debian.org@mirrors.aliyun.com@g' /etc/apt/sources.list.d/debian.sources

RUN \
    apt-get update \
    # Install dependencies
    && apt-get install -y --no-install-recommends \
        # basic environment
        curl nodejs libgmp-dev libmpfr-dev libmpc-dev \
        # For Security
        expat libldap-2.5-0 perl libsqlite3-0 zlib1g \
        # install fonts to support the use of tools like pypdfium2
        fonts-noto-cjk \
        # install a package to improve the accuracy of guessing mime type and file extension
        media-types \
        # install libmagic to support the use of python-magic guess MIMETYPE
        libmagic1 \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Copy Python environment and packages
ENV VIRTUAL_ENV=/app/api/.venv
COPY --from=packages ${VIRTUAL_ENV} ${VIRTUAL_ENV}
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

# Download nltk data
RUN mkdir -p /app/api/nltk_data && \
    python -c "import nltk; \
        downloader = nltk.downloader.Downloader('https://mirrors.tuna.tsinghua.edu.cn/nltk_data/'); \
        downloader.download('punkt', download_dir='/app/api/nltk_data'); \
        downloader.download('averaged_perceptron_tagger', download_dir='/app/api/nltk_data'); \
    "

ENV TIKTOKEN_CACHE_DIR=/app/api/.tiktoken_cache

RUN python -c "import tiktoken; tiktoken.encoding_for_model('gpt2')"

# Copy source code
COPY . /app/api/

# Copy entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ARG COMMIT_SHA
ENV COMMIT_SHA=${COMMIT_SHA}

ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
```

## 3. 启动服务

使用 docker 启动服务：

```bash
cd docker
cp .env.example .env

# 修改.env配置
## VECTOR_STORE=oceanbase
## OCEANBASE_ENABLE_HYBRID_SEARCH=true
## OCEANBASE_FULLTEXT_PARSER=japanese_ftparser
## COMPOSE_PROFILES=${VECTOR_STORE:-oceanbase}

# 启动服务
docker-compose up -d --build
```

### 安装日语分词器插件

```bash
# 登录容器
docker exec -it oceanbase bash
# 下载日语分词器插件
yum install -y wget
wget https://obcommunitydevtest.oss-cn-hangzhou.aliyuncs.com/dev/jp_ftparser.tar
# 解压
tar -xvf jp_ftparser.tar

# 安装分词器
mkdir -p /root/ob/observer/plugin_dir
cp jp_ftparser/libjapanese_ftparser.so /root/ob/observer/plugin_dir/
cp -r jp_ftparser/java /root/ob/observer/java

# 安装 Java 依赖
yum install java-1.8.0-openjdk-devel -y

# 激活插件
obclient -h127.0.0.1 -P2881 -uroot@sys -pdifyai123456
ALTER SYSTEM SET plugins_load='libjapanese_ftparser.so:on';

# 重启数据库
docker compose restart oceanbase

# 重启后检查 插件是否安装成功
docker exec -it oceanbase bash
obclient -h127.0.0.1 -P2881 -uroot@sys -pdifyai123456
SELECT * FROM oceanbase.GV$OB_PLUGINS WHERE NAME = 'japanese_ftparser';
```

## 4. 寻找语料建立知识库测试

参考 OceanBase 日本官方网站获取日语语料：[https://jp.oceanbase.com/docs/oceanbase-database](https://jp.oceanbase.com/docs/oceanbase-database)

