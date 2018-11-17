import PropTypes from 'prop-types';
import React, {Component} from "react";

import '../../css/traffic-info.css';
import {printable_address} from "../utils/addresses";

export default class TrafficInfo extends Component {
    render() {
        const goal = this.props.goal;
        let idx = 0;

        let goal_traffic = (goal.goal || []).slice();
        let current_traffic = (goal.state || []).slice();

        let rows = [];
        let next_goal, next_current, this_goal, this_current;
        while (true) {
            if (goal_traffic.length > 0) {
                next_goal = goal_traffic[0].join('-');
            } else {
                next_goal = '';
            }
            if (current_traffic.length > 0) {
                next_current = current_traffic[0].join('-');
            } else {
                next_current = '';
            }

            if (!next_goal && !next_current) {
                // The end!
                break;
            }

            if (next_goal === next_current) {
                // This is expected!
                this_goal = goal_traffic.shift();
                this_current = current_traffic.shift();

                rows.push(<tr key={idx++}>
                    <td className="pass address">{printable_address(this_goal[0])}</td>
                    <td className="pass">to</td>
                    <td className="pass address">{printable_address(this_goal[1])}</td>

                    <td className="pass address">{printable_address(this_current[0])}</td>
                    <td className="pass">to</td>
                    <td className="pass address">{printable_address(this_current[1])}</td>
                </tr>);
            } else if (!next_current || (next_goal && next_goal < next_current)) {
                // The next goal is missing from current traffic
                this_goal = goal_traffic.shift();
                rows.push(<tr key={idx++}>
                    <td className="fail address">{printable_address(this_goal[0])}</td>
                    <td className="fail">to</td>
                    <td className="fail address">{printable_address(this_goal[1])}</td>
                    <td className="fail" colSpan={3}>These packets are missing</td>
                </tr>);
            } else if (!next_goal || (next_current && next_current < next_goal)) {
                // The next current is not expected in the goal
                this_current = current_traffic.shift();
                rows.push(<tr key={idx++}>
                    <td className="fail" colSpan={3}>These packets shouldn't be received</td>
                    <td className="fail address">{printable_address(this_current[0])}</td>
                    <td className="fail">to</td>
                    <td className="fail address">{printable_address(this_current[1])}</td>
                </tr>);
            }
        }

        if (rows.length === 0) {
            // noinspection JSUnusedAssignment
            rows.push(<tr key={idx++}>
                <td className="pass" colSpan={3}>No packets expected</td>
                <td className="pass" colSpan={3}>✓ No packets received</td>
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

TrafficInfo.propTypes = {
    goal: PropTypes.object.isRequired,
};
