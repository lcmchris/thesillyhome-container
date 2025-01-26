import adapter from '@sveltejs/adapter-node';
import preprocess from 'svelte-preprocess';

/** @type {import('@sveltejs/kit').Config} */
const config = {
    preprocess: preprocess(),

    kit: {
        adapter: adapter(),
        paths: {
            base: process.env.INGRESS_ENTRY || '', // Dynamische Basis-URL für Ingress
        },
        vite: {
            server: {
                fs: {
                    allow: ['static'], // Zugriff auf das 'static/'-Verzeichnis erlauben
                },
            },
        },
    },
};

export default config;
