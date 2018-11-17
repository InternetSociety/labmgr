import {convert_nodes, convert_state} from "../../utils/node_state";
import * as actions from './actions';

const initialState = {};

export function exercise(state = initialState, action) {
    switch (action.type) {
        case actions.SET_EXERCISE:
            return {
                ...state,
                ...action.exercise,
                nodes: convert_nodes(action.exercise.nodes),
            };

        case actions.UPDATE_NODE_STATE:
            if (!state.nodes[action.node_id] || !state.nodes[action.node_id].state[action.goal_type])
                return state;

            return {
                ...state,
                nodes: {
                    ...state.nodes,
                    [action.node_id]: {
                        ...state.nodes[action.node_id],
                        state: {
                            ...state.nodes[action.node_id].state,
                            [action.goal_type]: {
                                ...state.nodes[action.node_id].state[action.goal_type],
                                state: convert_state(action.goal_type, action.state),
                                last_update: action.last_update,
                            }
                        }
                    }
                }
            };

        default:
            return state;
    }
}
