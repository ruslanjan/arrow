const path = require('path');

module.exports = {
    entry: './assets/js/main.js',
    mode: "development",
    output: {
        filename: 'bundle.js',
        path: __dirname + '/static/bundle',
        library: 'ui',
        libraryTarget: 'var',
    },
    module: {
        rules: [
            {
                test: /\.s[ac]ss$/i,
                use: [// Creates `style` nodes from JS strings
                    'style-loader',
                    // Translates CSS into CommonJS
                    'css-loader',
                    // Compiles Sass to CSS
                    'sass-loader',
                    // 'postcss-loader'
                ]
            },
            {
                test: /\.css$/i,
                use: ['style-loader', 'css-loader', 'postcss-loader'],
            },
        ]
    }
};