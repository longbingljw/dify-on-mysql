from core.variables.segments import ObjectSegment, Segment
from core.workflow.entities.variable_pool import VariablePool, VariableValue


def append_variables_recursively(
    pool: VariablePool, node_id: str, variable_key_list: list[str], variable_value: VariableValue | Segment
):
    """
    Append variables recursively
    
    This function adds a variable to the pool and ensures that nested dictionary/object 
    values can be accessed through the VariablePool's get() method with extended selectors.
    
    Note: Since VariablePool.add() only accepts 2-element selectors (node_id, variable_name),
    this function only stores the top-level variable. Nested access is handled by 
    VariablePool.get() method's built-in nested attribute navigation.
    
    :param pool: variable pool to append variables to
    :param node_id: node id
    :param variable_key_list: variable key list (only the first element is used for storage)
    :param variable_value: variable value
    :return:
    """
    # Only store the top-level variable to comply with VariablePool.add() constraints
    # The variable_key_list should have exactly one element for the variable name
    if len(variable_key_list) != 1:
        raise ValueError(f"variable_key_list must have exactly 1 element, got {len(variable_key_list)}")
    
    pool.add([node_id, variable_key_list[0]], variable_value)
