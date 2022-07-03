export const manifest = {
	appDir: "_app",
	assets: new Set(["data/light.bathroom_lights_tree.png","data/light.bedroom_ceiling_light_tree.png","data/light.bedroom_sidetable_lamp_tree.png","data/light.corridor_lights_tree.png","data/switch.livingroom_entrance_switch_center_tree.png","data/switch.livingroom_entrance_switch_left_tree.png","data/switch.livingroom_entrance_switch_right_tree.png","favicon.svg","icons/light_icon.svg","smui-dark.css","smui.css"]),
	mimeTypes: {".png":"image/png",".svg":"image/svg+xml",".css":"text/css"},
	_: {
		entry: {"file":"start-4cfb7b03.js","js":["start-4cfb7b03.js","chunks/index-e02e635c.js","chunks/index-3e58225d.js"],"css":[]},
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
			},
			{
				type: 'endpoint',
				id: "api/ImageFetch",
				pattern: /^\/api\/ImageFetch\/?$/,
				names: [],
				types: [],
				load: () => import('./entries/endpoints/api/ImageFetch.ts.js')
			}
		],
		matchers: async () => {
			
			return {  };
		}
	}
};
