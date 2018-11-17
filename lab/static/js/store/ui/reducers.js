import * as actions from './actions';

const initialState = {
    active_tab: 'instructions',
};

export function ui(state = initialState, action) {
    switch (action.type) {
        case actions.SET_ACTIVE_TAB:
            return {
                ...state,
                active_tab: action.active_tab,
            };

        default:
            return state;
    }
}
