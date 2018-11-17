import * as actions from './actions';

const initialState = {
    query_response: '',
    update_response: '',
};

export function irr(state = initialState, action) {
    switch (action.type) {
        case actions.SET_QUERY_RESPONSE:
            return {
                ...state,
                query_response: action.response,
            };

        case actions.SET_UPDATE_RESPONSE:
            return {
                ...state,
                update_response: action.response,
            };

        default:
            return state;
    }
}
