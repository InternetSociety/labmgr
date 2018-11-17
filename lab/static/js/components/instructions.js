import PropTypes from 'prop-types';
import React, {Component} from "react";
import showdown from 'showdown';
import '../../css/instructions.css';

export default class Instructions extends Component {
    render() {
        let converter = new showdown.Converter({openLinksInNewWindow: true});
        let text = this.props.text || '';
        return <div className="instructions" dangerouslySetInnerHTML={{__html: converter.makeHtml(text)}}/>
    }
}

Instructions.propTypes = {
    text: PropTypes.string,
};
