import * as actions from './actions';

const initialState = {
    scene_width: 0,
    scene_height: 0,
    drawings: [],
};

export function diagram(state = initialState, action) {
    switch (action.type) {
        case actions.SET_DIAGRAM:
            return action.diagram;

        default:
            return state;
    }
}
