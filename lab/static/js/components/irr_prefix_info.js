import PropTypes from 'prop-types';
import React, {Component} from "react";
import {printable_prefix} from "../utils/addresses";
import {compare_prefixes} from "../utils/node_state";

export default class IRRPrefixInfo extends Component {
    render() {
        const goal = this.props.goal;
        let idx = 0;

        let goal_prefixes = (goal.goal || []).slice();
        let current_prefixes = (goal.state || []).slice();

        let rows = [];
        let next_goal, next_current;
        while (true) {
            if (goal_prefixes.length > 0) {
                next_goal = goal_prefixes[0];
            } else {
                next_goal = null;
            }
            if (current_prefixes.length > 0) {
                next_current = current_prefixes[0];
            } else {
                next_current = null;
            }

            if (!next_goal && !next_current) {
                // The end!
                break;
            }

            if (!next_goal) next_goal = {};
            if (!next_current) next_current = {};

            let cmp = compare_prefixes(next_goal, next_current);
            if (cmp === 0) {
                // This is expected!
                goal_prefixes.shift();
                current_prefixes.shift();

                rows.push(<tr key={idx++}>
                    <td className="pass">
                        <span className="address">
                            {printable_prefix(next_goal.prefix, next_goal.prefix_length)}
                        </span>
                    </td>

                    <td className="pass">
                        <span className="address">
                            {printable_prefix(next_current.prefix, next_current.prefix_length)}
                        </span>
                    </td>
                </tr>);
            } else if (!next_current || (next_goal && cmp < 0)) {
                // The next goal is missing from current routes
                goal_prefixes.shift();
                rows.push(<tr key={idx++}>
                    <td className="fail">
                        <span className="address">
                            {printable_prefix(next_goal.prefix, next_goal.prefix_length)}
                        </span>
                    </td>
                    <td className="fail">This prefix is missing</td>
                </tr>);
            } else if (!next_goal || (next_current && cmp > 0)) {
                // The next current is not expected in the goal
                current_prefixes.shift();
                rows.push(<tr key={idx++}>
                    <td className="fail">This prefix shouldn't be included</td>
                    <td className="fail">
                        <span className="address">
                            {printable_prefix(next_current.prefix, next_current.prefix_length)}
                        </span>
                    </td>
                </tr>);
            }
        }

        if (rows.length === 0) {
            // noinspection JSUnusedAssignment
            rows.push(<tr key={idx++}>
                <td className="pass">No prefixes expected</td>
                <td className="pass">✓ No prefixes included</td>
            </tr>);
        }

        return <table className="traffic">
            <colgroup className="expected">
                <col span={1}/>
            </colgroup>
            <colgroup className="current">
                <col span={1}/>
            </colgroup>

            <thead>
                <tr>
                    <th>Expected</th>
                    <th>Currently seen</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>;
    }
}

IRRPrefixInfo.propTypes = {
    goal: PropTypes.object.isRequired,
};
