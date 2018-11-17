import Cookie from "js-cookie";
import moment from "moment-timezone";
import PropTypes from 'prop-types';
import PubSub from "pubsub-js";
import React, {Component} from "react";
import connect from "react-redux/es/connect/connect";
import {bindActionCreators} from "redux";
import showdown from "showdown";
import '../../css/irr-node.css';
import {setQueryResponse, setUpdateResponse} from "../store/irr/actions";
import IRRNeighborInfo from "./irr_neighbor_info";
import IRRPrefixInfo from "./irr_prefix_info";


class IRRNode extends Component {
    constructor(props) {
        super(props);

        this.sendQuery = this.sendQuery.bind(this);
        this.sendUpdate = this.sendUpdate.bind(this);
    }

    componentDidMount() {
        // this.term = new Terminal({cursorBlink: true, cursorStyle: 'block', cols: 80, rows: 24});
        // this.term.open(this.refs.terminal);
        // this.term.on("data", (data) => {
        //     try {
        //         this.props.websocket.json({type: 'terminal-input', node_id: this.props.node.id, data});
        //     } catch (e) {
        //         // That was best-effort
        //     }
        // });
        // this.token = PubSub.subscribe("terminal-output-" + this.props.node.id, (evt, data) => {
        //     this.term.write(atob(data));
        // });
    }

    componentWillUnmount() {
        this.term && this.term.dispose();
        this.token && PubSub.unsubscribe(this.token);
    }

    sendQuery(evt) {
        this.props.actions.setQueryResponse('Loading...');
        this.props.websocket.json({
            type: 'irr-query',
            node_id: this.props.node.id,
            query: this.refs.query.value,
        });
        evt.preventDefault();
    }

    sendUpdate(evt) {
        this.props.actions.setUpdateResponse('Loading...');
        this.props.websocket.json({
            type: 'irr-update',
            node_id: this.props.node.id,
            update: this.refs.update.value,
        });
        evt.preventDefault();
    }

    render() {
        // Hack to get the terminal to initialise properly
        // setTimeout(() => {
        //     if (!this.term) return;
        //     this.term.resize(80, 24);
        // }, 10);

        let goals = [];
        let idx = 0;

        for (const [goal_type, goal] of Object.entries(this.props.node.state)) {
            let goal_info, note;
            switch (goal_type) {
                case 'ASN IPv4':
                case 'ASN IPv6':
                case 'AS-SET IPv4':
                case 'AS-SET IPv6':
                    note = null;
                    goal_info = <IRRPrefixInfo goal={goal}/>;
                    break;

                case 'NEIGHBORS':
                    note=<p>
                        <b>Note:</b> This training system only supports simple "<code>mp-import: from A accept
                        B</code>" and "<code>mp-export: to X announce Y</code>" style policy rules. Please limit
                        yourself to that type of policy for this training.
                    </p>;
                    goal_info = <IRRNeighborInfo goal={goal}/>;
                    break;

                default:
                    continue;
            }
            // noinspection JSUnresolvedFunction
            let last_update = moment(goal.last_update).format('H:mm:ss');

            goals.push(<div key={idx++} style={{display: "block", flexDirection: "column"}}>
                <h2>{goal.goal_type_display} (last change at {last_update})</h2>
                {note}
                {goal_info}
            </div>);
        }

        let converter = new showdown.Converter({openLinksInNewWindow: true});
        let instructions = this.props.node.info.instructions || '';

        return <div className="irr-node">
            <div dangerouslySetInnerHTML={{__html: converter.makeHtml(instructions)}}/>

            <h1>Query the IRR database</h1>
            <p>
                You can search the IRR database here using <code>whois</code> queries. You can search for example on
                IP address, AS Number, AS-Set or contact handle.
            </p>

            <form onSubmit={this.sendQuery}>
                <label>Query: </label>
                <input name="query" ref="query" placeholder="e.g. AS64500"/>
                <button type="submit">Send</button>
            </form>

            {this.props.irr.query_response ? <div className="query-response">
                {this.props.irr.query_response.trim()}
            </div> : null}

            <h1>Updating the IRR</h1>

            {this.props.node.info.maintainer ?
                <div><b>Maintainer object:</b> {this.props.node.info.maintainer}<br/></div> : null}
            {this.props.node.info.maintainer_password ?
                <div><b>Maintainer password:</b> {this.props.node.info.maintainer_password}<br/></div> : null}

            <form onSubmit={this.sendUpdate}>
                <div className="update-area">
                    <textarea className="update-text" ref="update" placeholder="Type your IRR objects here"/>
                    <div className="update-response">
                        {this.props.irr.update_response}
                    </div>
                </div>
                <button type="submit">Submit update to IRR</button>
            </form>

            <h1>Currently in the IRR</h1>
            {goals}

            {/*
            <h1>Terminal</h1>
            <p>
                This terminal can optionally be used to run command line utilities
                like <code>whois</code> and <code>bgpq3</code>.
            </p>

            {this.props.node.info.username ?
                <div><b>Username:</b> {this.props.node.info.username}<br/></div> : null}
            {this.props.node.info.password ?
                <div><b>Password:</b> {this.props.node.info.password}<br/></div> : null}

            <br/>

            <div style={{display: 'flex'}}>
                <div ref="terminal" style={{backgroundColor: 'black', padding: 10}}></div>
            </div>
            */}

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


IRRNode.propTypes = {
    websocket: PropTypes.object.isRequired,
    irr: PropTypes.shape({
        query_response: PropTypes.string.isRequired,
        update_response: PropTypes.string.isRequired,
    }),
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

function mapStateToProps(state) {
    return {
        irr: state.irr,
    };
}

function mapDispatchToProps(dispatch) {
    return {
        actions: bindActionCreators({
            setQueryResponse,
            setUpdateResponse,
        }, dispatch)
    }
}

export default connect(mapStateToProps, mapDispatchToProps)(IRRNode);
