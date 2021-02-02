module.exports = {
	// mode: "development || "production",
	module: {
		entry: {
			main: 'coffee/aivoice.coffee'
		},
		output: {
			filename: 'code/modules/html_interface/[name].js',
			path: path.resolve(__dirname, 'tmp/packed'),
			assetModuleFilename: 'assets/[name]-[contenthash][ext][query]'
		},
		rules: [
			{
				test: /\.coffee$/,
				loader: "coffee-loader"
				options: {
					bare: false,
					transpile: {
					  presets: ["@babel/env"],
					  plugins: ["@babel/plugin-transform-arrow-functions"]
					}
				}
			}
		]
	},
	resolve: {
		extensions: [".coffee", ".js"]
	}
};
