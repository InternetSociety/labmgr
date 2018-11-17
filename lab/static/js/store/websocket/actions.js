/*
 * action types
 */
export const SET_WS_CONNECTED = 'SET_WS_CONNECTED';

/*
 * action creators
 */
export function setWSConnected(connected) {
    return {type: SET_WS_CONNECTED, connected}
}
