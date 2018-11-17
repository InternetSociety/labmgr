import * as actions from './actions';

const initialState = {
    connected: false,
};

export function websocket(state = initialState, action) {
    switch (action.type) {
        case actions.SET_WS_CONNECTED:
            return {
                ...state,
                connected: action.connected,
            };

        default:
            return state;
    }
}
