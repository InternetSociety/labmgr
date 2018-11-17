/*
 * action types
 */
export const SET_EXERCISE = 'SET_EXERCISE';
export const UPDATE_NODE_STATE = 'UPDATE_NODE_STATE';

/*
 * action creators
 */
export function setExercise(exercise) {
    return {type: SET_EXERCISE, exercise}
}

export function updateNodeState(node_id, goal_type, state, last_update) {
    return {type: UPDATE_NODE_STATE, node_id, goal_type, state, last_update}
}
