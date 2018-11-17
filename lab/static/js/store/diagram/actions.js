/*
 * action types
 */
export const SET_DIAGRAM = 'SET_DIAGRAM';

/*
 * action creators
 */
export function setDiagram(diagram) {
    return {type: SET_DIAGRAM, diagram}
}
