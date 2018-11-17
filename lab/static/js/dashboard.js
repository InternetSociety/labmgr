import React from 'react'
import ReactDOM from 'react-dom'
import {addLocaleData, IntlProvider} from 'react-intl';
import nlLocaleData from 'react-intl/locale-data/nl';
import {Provider} from 'react-redux'
import 'react-tabs/style/react-tabs.css'
import {combineReducers, createStore} from 'redux'

import App from './components/dashboard_app'
import {diagram} from './store/diagram/reducers'
import {exercise} from './store/exercise/reducers'
import {irr} from './store/irr/reducers'
import {ui} from './store/ui/reducers'
import {websocket} from './store/websocket/reducers'

addLocaleData(nlLocaleData);

const rootReducer = combineReducers({
    exercise,
    diagram,
    irr,
    ui,
    websocket,
});

// noinspection JSUnresolvedVariable
const store = createStore(
    rootReducer,
    window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__()
);


ReactDOM.render(
    <IntlProvider locale={navigator.language}>
        <Provider store={store}>
            <App/>
        </Provider>
    </IntlProvider>,
    document.getElementById('react')
);
