import PropTypes from 'prop-types';
import PubSub from 'pubsub-js'
import React, {Component} from "react";
import showdown from "showdown";
import {Terminal} from 'xterm';
import 'xterm/src/xterm.css';
import '../../css/work-node.css';
import Cookie from 'js-cookie';

export default class WorkNode extends Component {
    componentDidMount() {
        this.term = new Terminal({cursorBlink: true, cursorStyle: 'block', cols: 81, rows: 30});
        this.term.open(this.refs.terminal);
        this.term.on("data", (data) => {
            try {
                this.props.websocket.json({type: 'terminal-input', 'node_id': this.props.node.id, data});
            } catch (e) {
                // That was best-effort
            }
        });
        this.token = PubSub.subscribe("terminal-output-" + this.props.node.id, (evt, data) => {
            this.term.write(atob(data));
        });
    }

    componentWillUnmount() {
        this.term && this.term.dispose();
        this.token && PubSub.unsubscribe(this.token);
    }

    render() {
        // Hack to get the terminal to initialise properly
        setTimeout(() => {
            if (!this.term) return;
            this.term.resize(81, 30);
            this.term.focus();
        }, 10);

        let converter = new showdown.Converter({openLinksInNewWindow: true});
        let instructions = this.props.node.info.instructions || '';

        return <div className="work-node">
            <div dangerouslySetInnerHTML={{__html: converter.makeHtml(instructions)}}/>

            {this.props.node.info.username ? <div><b>Username:</b> {this.props.node.info.username}<br/></div> : null}
            {this.props.node.info.password ? <div><b>Password:</b> {this.props.node.info.password}<br/></div> : null}

            <br/>
            <div style={{display: 'flex'}}>
                <div ref="terminal" style={{backgroundColor: 'black', padding: 10}}></div>
            </div>

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

WorkNode.propTypes = {
    websocket: PropTypes.object.isRequired,
    node: PropTypes.shape({
        id: PropTypes.number,
        gns3_id: PropTypes.string,
        name: PropTypes.string,
        type: PropTypes.string,
        info: PropTypes.shape({
            username: PropTypes.string,
            password: PropTypes.string,
            instructions: PropTypes.string,
        }),
    }),
};
