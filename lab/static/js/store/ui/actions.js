/*
 * action types
 */
export const SET_ACTIVE_TAB = 'SET_ACTIVE_TAB';

/*
 * action creators
 */
export function setActiveTab(active_tab) {
    return {type: SET_ACTIVE_TAB, active_tab}
}
