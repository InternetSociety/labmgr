import Cookie from "js-cookie";
import moment from 'moment-timezone';
import PropTypes from 'prop-types';
import React, {Component} from "react";
import showdown from "showdown";
import '../../css/monitor-node.css';
import RouteInfo from "./route_info";
import TrafficInfo from "./traffic_info";

export default class MonitorNode extends Component {
    render() {
        let idx = 0;
        let goals = [];

        for (const [goal_type, goal] of Object.entries(this.props.node.state)) {
            let goal_info;
            switch (goal_type) {
                case 'Routes IPv4':
                case 'Routes IPv6':
                    goal_info = <RouteInfo goal={goal}/>;
                    break;

                case 'Received traffic':
                    goal_info = <TrafficInfo goal={goal}/>;
                    break;

                default:
                    continue;
            }
            // noinspection JSUnresolvedFunction
            let last_update = moment(goal.last_update).format('H:mm:ss');

            goals.push(<div key={idx++} style={{display: "block", flexDirection: "column"}}>
                <h2>{goal.goal_type_display} (last change at {last_update})</h2>
                {goal_info}
            </div>);
        }

        let converter = new showdown.Converter({openLinksInNewWindow: true});
        let instructions = this.props.node.info.instructions || '';

        return <div className="monitor-node">
            <div dangerouslySetInnerHTML={{__html: converter.makeHtml(instructions)}}/>

            <h1>Looking glass from this router's viewpoint</h1>
            {goals}

            <br/>

            For emergencies:
            <button style={{color: 'red'}} onClick={() => {
                if (confirm('Are you sure you want to reboot this device?')) {
                    const url = 'https://' + window.location.hostname + '/lab/node/' + this.props.node.id + '/reload/';
                    fetch(url, {
                        method: 'POST',
                        credentials: 'same-origin',
                        headers: {
                            'X-CSRFToken': Cookie.get('csrftoken'),
                        }
                    }).then().catch();
                }
            }}>reboot device</button>
        </div>
    }
}

MonitorNode.propTypes = {
    node: PropTypes.shape({
        id: PropTypes.number,
        gns3_id: PropTypes.string,
        name: PropTypes.string,
        type: PropTypes.string,
        state: PropTypes.objectOf(PropTypes.shape({
            goal_type: PropTypes.string,
            state: PropTypes.any,
            goal: PropTypes.any,
            last_update: PropTypes.string,
        })),
    }),
};
