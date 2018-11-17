let path = require("path");
let BundleTracker = require('webpack-bundle-tracker');
let webpack = require('webpack');

// noinspection JSUnresolvedFunction
module.exports = {
    context: __dirname,
    devtool: 'source-map',
    node: {
        fs: 'empty'
    },
    entry: {
        dashboard: './lab/static/js/dashboard',
    },

    output: {
        path: path.resolve('./lab/static/bundles/'),
        filename: "[name]-[chunkhash].js",
    },
    optimization: {
        splitChunks: {
            cacheGroups: {
                vendors: {
                    test: /[\\/]node_modules[\\/]/,
                    name: 'vendors',
                    chunks: 'all',
                },
            }
        }
    },
    plugins: [
        new BundleTracker({filename: './webpack-stats.json'}),
        new webpack.IgnorePlugin(/^\.\/.*js.map$/, /.*xterm\/dist\/addons/),
    ],
    module: {
        rules: [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                use: ['babel-loader']
            },
            {
                test: /\.css$/,
                use: ['style-loader', 'css-loader']
            }
        ]
    },
    resolve: {
        extensions: ['*', '.js', '.jsx']
    }
};
