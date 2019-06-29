import css from 'css';
import transform_css from 'css-to-react-native';
import React, {Component} from "react";
import {connect} from 'react-redux'
import {bindActionCreators} from 'redux';
import '../../css/project-diagram.css';
import {setActiveTab} from '../store/ui/actions';


class ProjectDiagram extends Component {
    static convertStyle(style) {
        let parsed = css.parse('.label {' + style + '}');
        let lines = [];
        for (let line of parsed.stylesheet.rules[0].declarations) {
            lines.push([line.property, line.value]);
        }
        return transform_css(lines);
    }

    getDrawings() {
        let drawings = [];

        let idx = 0;
        for (let drawing of this.props.diagram.drawings) {
            if (drawing.svg === '<svg></svg>') continue;

            let style = {
                left: drawing.x,
                top: drawing.y,
                zIndex: drawing.z,
                transform: 'rotate(' + drawing.rotation + 'deg)',
            };

            drawings.push(<div key={idx} className="drawing element" style={style}
                               dangerouslySetInnerHTML={{__html: drawing.svg}}/>);
            idx++;
        }

        return drawings;
    }

    getLinks() {
        let links = [];

        let idx = 0;
        for (let link of this.props.diagram.links) {
            if (link.label1.text || link.label2.text) {
                links.push(<line key={idx}
                                 x1={link.x1 + link.x1_offset} y1={link.y1 + link.y1_offset}
                                 x2={link.x2 + link.x2_offset} y2={link.y2 + link.y2_offset}
                                 style={{stroke: "rgb(0,0,0)", strokeWidth: 3}}/>);
            }
            idx++;
        }
        return <svg className="link element"
                    width={this.props.diagram.scene_width}
                    height={this.props.diagram.scene_height}>{links}</svg>;
    }

    getLinkLabels() {
        let link_labels = [];

        let idx = 0;
        for (let link of this.props.diagram.links) {
            if (link.label1.text && !link.label1.text.includes('_')) {
                let style = {
                    left: link.x1 + link.label1.x,
                    top: link.y1 + link.label1.y,
                    transform: 'rotate(' + link.label1.rotation + 'deg)',
                    ... ProjectDiagram.convertStyle(link.label1.style),
                };

                link_labels.push(<div key={idx} className="label element" style={style}>
                    {link.label1.text}
                </div>);
                idx++;
            }
            if (link.label2.text && !link.label2.text.includes('_')) {
                let style = {
                    left: link.x2 + link.label2.x,
                    top: link.y2 + link.label2.y,
                    transform: 'rotate(' + link.label2.rotation + 'deg)',
                    ... ProjectDiagram.convertStyle(link.label2.style),
                };

                link_labels.push(<div key={idx} className="link-label element" style={style}>
                    {link.label2.text}
                </div>);
                idx++;
            }
        }

        return link_labels;
    }

    getNodes() {
        let nodes = [];

        let idx = 0;
        for (let node of this.props.diagram.nodes) {
            if (!node.label.text.includes('_')) {
                let style = {
                    width: node.width,
                    height: node.height,
                    left: node.x,
                    top: node.y,
                    zIndex: node.z,
                    cursor: 'pointer',
                    };

                if (this.props.ui.active_tab === node.node_id) {
                    style.filter =
                        'drop-shadow(-1px -1px 1px white) ' +
                        'drop-shadow(-1px 1px 1px white) ' +
                        'drop-shadow(1px -1px 1px white) ' +
                        'drop-shadow(1px 1px 1px white)' +
                        'drop-shadow(0 0 1px #369)'
                }

                let src = '/lab/symbols/' + node.symbol;
                nodes.push(<img onClick={() => this.props.actions.setActiveTab(node.node_id)} key={idx}
                                className="node element" style={style} src={src}/>);
                idx++;

                if (node.label.text) {
                    let style = {
                        left: node.x + node.label.x,
                        top: node.y + node.label.y,
                        zIndex: node.z,
                        transform: 'rotate(' + node.label.rotation + 'deg)',
                        ...ProjectDiagram.convertStyle(node.label.style),
                    };

                    nodes.push(<div key={idx} className="node-label element" style={style}>
                        {node.label.text}
                    </div>);
                    idx++;
                }
            }
        }

        return nodes;
    }

    render() {
        if (!this.props.diagram.scene_width || !this.props.diagram.scene_height) {
            return null;
        }

        const container_style = {
            width: this.props.diagram.scene_width,
            height: this.props.diagram.scene_height,
        };
        const diagram_style = {
            minWidth: this.props.diagram.scene_width,
            minHeight: this.props.diagram.scene_height,
        };

        const drawings = this.getDrawings();
        const links = this.getLinks();
        const link_labels = this.getLinkLabels();
        const nodes = this.getNodes();

        return <div className="project-diagram-container" style={{...container_style, ...this.props.style}}>
            <div className="project-diagram" style={diagram_style}>
                {drawings}
                {links}
                {link_labels}
                {nodes}
            </div>
        </div>
    }
}


function mapStateToProps(state) {
    return {
        diagram: state.diagram,
        ui: state.ui,
    };
}

function mapDispatchToProps(dispatch) {
    return {
        actions: bindActionCreators({
            setActiveTab
        }, dispatch)
    }
}

export default connect(mapStateToProps, mapDispatchToProps)(ProjectDiagram);
