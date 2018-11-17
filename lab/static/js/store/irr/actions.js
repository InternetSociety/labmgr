/*
 * action types
 */
export const SET_QUERY_RESPONSE = 'SET_QUERY_RESPONSE';
export const SET_UPDATE_RESPONSE = 'SET_UPDATE_RESPONSE';

/*
 * action creators
 */
export function setQueryResponse(response) {
    return {type: SET_QUERY_RESPONSE, response}
}

export function setUpdateResponse(response) {
    return {type: SET_UPDATE_RESPONSE, response}
}
