import PropTypes from 'prop-types';
import React, {Component} from "react";
import '../../css/irr-neighbor-info.css';
import {compare} from "../utils/node_state";

export default class IRRNeighborInfo extends Component {
    render() {
        const goal = this.props.goal;
        let idx = 0;

        let neighbors = [...Object.keys(goal.goal), ...Object.keys(goal.state)];
        neighbors = [...new Set(neighbors)];
        neighbors.sort();

        let rows = [];
        for (let neighbor of neighbors) {
            const current_goal = goal.goal[neighbor] || {import: [], export: []};
            const current_state = goal.state[neighbor] || {import: [], export: []};

            let cmp = compare(current_goal, current_state);
            let className = cmp === 0 ? 'pass' : 'fail';

            rows.push(<tr key={idx++}>
                <td className={className}><span className="address">{neighbor}</span></td>
                <td className={className}>{current_goal.import.map(a => a.toString()).join(', ')}</td>
                <td className={className}>{current_goal.export.map(a => a.toString()).join(', ')}</td>
                <td className={className}>{current_state.import.map(a => a.toString()).join(', ')}</td>
                <td className={className}>{current_state.export.map(a => a.toString()).join(', ')}</td>
            </tr>);
        }

        if (rows.length === 0) {
            // noinspection JSUnusedAssignment
            rows.push(<tr key={idx++}>
                <td className="pass"></td>
                <td className="pass" colSpan={2}>No neighbors expected</td>
                <td className="pass" colSpan={2}>✓ No neighbors defined</td>
            </tr>);
        }

        return <table className="neighbor">
            <colgroup className="expected">
                <col span={1}/>
            </colgroup>
            <colgroup className="current">
                <col span={1}/>
            </colgroup>
            <colgroup>
                <col span={1}/>
            </colgroup>
            <colgroup className="current">
                <col span={1}/>
            </colgroup>
            <colgroup>
                <col span={1}/>
            </colgroup>

            <thead>
                <tr>
                    <th>Neighbor</th>
                    <th colSpan={2}>Expected</th>
                    <th colSpan={2}>Currently seen</th>
                </tr>
                <tr>
                    <th>ASN</th>
                    <th>Import</th>
                    <th>Export</th>
                    <th>Import</th>
                    <th>Export</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>;
    }
}

IRRNeighborInfo.propTypes = {
    goal: PropTypes.object.isRequired,
};
