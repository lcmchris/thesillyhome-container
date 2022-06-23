export const manifest = {
	appDir: "_app",
	assets: new Set(["favicon.svg","icons/light_icon.svg","smui-dark.css","smui.css"]),
	mimeTypes: {".svg":"image/svg+xml",".css":"text/css"},
	_: {
		entry: {"file":"start-dba1e4f5.js","js":["start-dba1e4f5.js","chunks/index-718d9243.js"],"css":[]},
		nodes: [
			() => import('./nodes/0.js'),
			() => import('./nodes/1.js'),
			() => import('./nodes/5.js'),
			() => import('./nodes/2.js'),
			() => import('./nodes/3.js'),
			() => import('./nodes/4.js')
		],
		routes: [
			{
				type: 'page',
				id: "",
				pattern: /^\/$/,
				names: [],
				types: [],
				path: "/",
				shadow: null,
				a: [0,2],
				b: [1]
			},
			{
				type: 'page',
				id: "About Us",
				pattern: /^\/About Us\/?$/,
				names: [],
				types: [],
				path: "/About Us",
				shadow: null,
				a: [0,3],
				b: [1]
			},
			{
				type: 'page',
				id: "Controls",
				pattern: /^\/Controls\/?$/,
				names: [],
				types: [],
				path: "/Controls",
				shadow: () => import('./entries/endpoints/Controls.ts.js'),
				a: [0,4],
				b: [1]
			},
			{
				type: 'page',
				id: "Dashboard",
				pattern: /^\/Dashboard\/?$/,
				names: [],
				types: [],
				path: "/Dashboard",
				shadow: () => import('./entries/endpoints/Dashboard.ts.js'),
				a: [0,5],
				b: [1]
			}
		],
		matchers: async () => {
			
			return {  };
		}
	}
};
