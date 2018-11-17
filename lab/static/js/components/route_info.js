import PropTypes from 'prop-types';
import React, {Component} from "react";
import {printable_prefix} from "../utils/addresses";
import {compare_prefixes} from "../utils/node_state";

export default class RouteInfo extends Component {
    render() {
        const goal = this.props.goal;
        let idx = 0;

        let goal_routes = (goal.goal || []).slice();
        let current_routes = (goal.state || []).slice();

        let rows = [];
        let next_goal, next_current;
        while (true) {
            if (goal_routes.length > 0) {
                next_goal = goal_routes[0];
            } else {
                next_goal = null;
            }
            if (current_routes.length > 0) {
                next_current = current_routes[0];
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
                goal_routes.shift();
                current_routes.shift();

                rows.push(<tr key={idx++}>
                    <td className="pass">
                        <span className="address">
                            {printable_prefix(next_goal.prefix, next_goal.prefix_length)}
                        </span>
                        <br/>
                        <span className="extra">
                            AS-Path: {(next_goal['bgp.as_path'] || []).map(asn => asn.toString()).join(' ')}
                        </span>
                    </td>
                    <td className="pass"></td>
                    <td className="pass"></td>

                    <td className="pass">
                        <span className="address">
                            {printable_prefix(next_current.prefix, next_current.prefix_length)}
                        </span>
                        <br/>
                        <span className="extra">
                            AS-Path: {(next_current['bgp.as_path'] || []).map(asn => asn.toString()).join(' ')}
                        </span>
                    </td>
                    <td className="pass"></td>
                    <td className="pass"></td>
                </tr>);
            } else if (!next_current || (next_goal && cmp < 0)) {
                // The next goal is missing from current routes
                goal_routes.shift();
                rows.push(<tr key={idx++}>
                    <td className="fail">
                        <span className="address">
                            {printable_prefix(next_goal.prefix, next_goal.prefix_length)}
                        </span>
                        <br/>
                        <span className="extra">
                            AS-Path: {(next_goal['bgp.as_path'] || []).map(asn => asn.toString()).join(' ')}
                        </span>
                    </td>
                    <td className="fail"></td>
                    <td className="fail"></td>
                    <td className="fail" colSpan={3}>This route is missing</td>
                </tr>);
            } else if (!next_goal || (next_current && cmp > 0)) {
                // The next current is not expected in the goal
                current_routes.shift();
                rows.push(<tr key={idx++}>
                    <td className="fail" colSpan={3}>This route shouldn't be received</td>
                    <td className="fail">
                        <span className="address">
                            {printable_prefix(next_current.prefix, next_current.prefix_length)}
                        </span>
                        <br/>
                        <span className="extra">
                            AS-Path: {(next_current['bgp.as_path'] || []).map(asn => asn.toString()).join(' ')}
                        </span>
                    </td>
                    <td className="fail"></td>
                    <td className="fail"></td>
                </tr>);
            }
        }

        if (rows.length === 0) {
            // noinspection JSUnusedAssignment
            rows.push(<tr key={idx++}>
                <td className="pass" colSpan={3}>No routes expected</td>
                <td className="pass" colSpan={3}>✓ No routes received</td>
            </tr>);
        }

        return <table className="traffic">
            <colgroup className="expected">
                <col span={3}/>
            </colgroup>
            {/* Sigh, Safari gives every cell a border when you set a border on the colgroup */}
            <colgroup className="current">
                <col span={1}/>
            </colgroup>
            {/* So we put the other columns in a different group to keep Safari from messing it up */}
            <colgroup>
                <col span={2}/>
            </colgroup>

            <thead>
                <tr>
                    <th colSpan={3}>Expected</th>
                    <th colSpan={3}>Currently seen</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>;
    }
}

RouteInfo.propTypes = {
    goal: PropTypes.object.isRequired,
};
