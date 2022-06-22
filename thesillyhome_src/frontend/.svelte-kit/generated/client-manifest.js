export { matchers } from './client-matchers.js';

export const components = [
	() => import("..\\runtime\\components\\layout.svelte"),
	() => import("..\\runtime\\components\\error.svelte"),
	() => import("..\\..\\src\\routes\\About Us.svelte"),
	() => import("..\\..\\src\\routes\\Controls.svelte"),
	() => import("..\\..\\src\\routes\\Dashboard.svelte"),
	() => import("..\\..\\src\\routes\\index.svelte")
];

export const dictionary = {
	"": [[0, 5], [1]],
	"About Us": [[0, 2], [1]],
	"Controls": [[0, 3], [1], 1],
	"Dashboard": [[0, 4], [1], 1]
};