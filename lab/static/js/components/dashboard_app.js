import PubSub from 'pubsub-js'
import React, {Component, Fragment} from "react";
import {connect} from 'react-redux';
import {Tab, TabList, TabPanel, Tabs} from 'react-tabs';
import {bindActionCreators} from 'redux';
import Sockette from "sockette";

import '../../css/dashboard-app.css';
import {setDiagram} from "../store/diagram/actions";
import {setExercise, updateNodeState} from "../store/exercise/actions";
import {setQueryResponse, setUpdateResponse} from '../store/irr/actions';
import {setActiveTab} from '../store/ui/actions';
import {setWSConnected} from '../store/websocket/actions';
import {compare_states} from "../utils/node_state";
import ProjectDiagram from "./diagram";
import Instructions from './instructions';
import IRRNode from "./irr_node";
import MonitorNode from "./monitor_node";
import WorkNode from "./work_node";


class App extends Component {
    constructor(props) {
        super(props);
    }

    componentDidMount() {
        const exercise = JSON.parse(document.getElementById('exercise-data').textContent);
        this.props.actions.setExercise(exercise);

        const diagram = JSON.parse(document.getElementById('diagram-data').textContent);
        this.props.actions.setDiagram(diagram);

        this.ws = new Sockette('wss://' + window.location.hostname + '/ws/' + exercise.id + '/events', {
            'onopen': () => this.props.actions.setWSConnected(true),
            'onmessage': e => {
                let data = JSON.parse(e.data);
                switch (data.type) {
                    case 'state':
                        this.props.actions.updateNodeState(data.node, data.goal_type, data.content, data.ts);
                        break;

                    case 'terminal-output':
                        PubSub.publish("terminal-output-" + data.node_id, data.data);
                        break;

                    case 'irr-query-response':
                        this.props.actions.setQueryResponse(data['response']);
                        break;

                    case 'irr-update-response':
                        this.props.actions.setUpdateResponse(data['response']);
                        break;

                    default:
                        console.log(data);
                }
            },
            'onreconnect': e => console.log('Reconnecting...', e),
            'onmaximum': e => console.log('Stop Attempting!', e),
            'onclose': () => this.props.actions.setWSConnected(false),
            'onerror': e => console.log('Error:', e)
        });
    }

    componentWillUnmount() {
        this.ws.close();
    }

    render() {
        if (!this.props.exercise.id) {
            return null;
        }
        let tabs = [<Tab key="0">Instructions</Tab>];
        let panels = [<TabPanel key="0"><Instructions text={this.props.exercise.instructions}/></TabPanel>];
        let gns3_ids = {0: 'instructions'};

        let passed;
        let selected_idx = 0;
        let idx = 1;
        for (const node of Object.values(this.props.exercise.nodes)) {
            switch (node.type) {
                case 'WorkNode':
                    tabs.push(<Tab key={idx}>{node.name}</Tab>);
                    panels.push(<TabPanel key={idx}>
                        <WorkNode websocket={this.ws} node={node}/>
                    </TabPanel>);
                    break;

                case 'MonitorNode':
                    passed = compare_states(node.state);
                    tabs.push(<Tab key={idx} className={["react-tabs__tab", {pass: passed, fail: !passed}]}>
                        {node.name}
                    </Tab>);
                    panels.push(<TabPanel key={idx}>
                        <MonitorNode node={node}/>
                    </TabPanel>);
                    break;

                case 'IRRNode':
                    passed = compare_states(node.state);
                    tabs.push(<Tab key={idx} className={["react-tabs__tab", {pass: passed, fail: !passed}]}>
                        {node.name}
                    </Tab>);
                    panels.push(<TabPanel key={idx}>
                        <IRRNode websocket={this.ws} node={node}/>
                    </TabPanel>);
                    break;

                default:
                    // Skip this node
                    continue;
            }

            gns3_ids[idx] = node.gns3_id;
            if (node.gns3_id === this.props.ui.active_tab) {
                selected_idx = idx;
            }
            idx++;
        }

        let status;
        if (this.props.websocket.connected) {
            status = <li className="tab-status connected">Online</li>;
        } else {
            status = <li className="tab-status disconnected">Offline</li>;
        }

        return <Fragment>
            <div style={{flex: 1, display: 'flex'}}>
                <Tabs selectedIndex={selected_idx}
                      forceRenderTabPanel={true}
                      onSelect={tabIndex => this.props.actions.setActiveTab(gns3_ids[tabIndex])}
                      style={{flex: 1}}>
                    <TabList>
                        {tabs}

                        {status}
                    </TabList>

                    {panels}
                </Tabs>
            </div>
            <ProjectDiagram style={{height: 'auto'}}/>
        </Fragment>;
    }
}


function mapStateToProps(state) {
    return {
        exercise: state.exercise,
        irr: state.irr,
        ui: state.ui,
        websocket: state.websocket,
    };
}

function mapDispatchToProps(dispatch) {
    return {
        actions: bindActionCreators({
            setExercise,
            updateNodeState,
            setDiagram,
            setActiveTab,
            setWSConnected,
            setQueryResponse,
            setUpdateResponse,
        }, dispatch)
    }
}

export default connect(mapStateToProps, mapDispatchToProps)(App);
