import { defineConfig } from 'vite';
import { sveltekit } from '@sveltejs/kit/vite';

export default defineConfig({
    plugins: [sveltekit()],
    server: {
        mimeTypes: {
            '.css': 'text/css', // Sicherstellen, dass CSS-Dateien korrekt geladen werden
        },
        fs: {
            strict: true, // Zugriff auf das Dateisystem einschränken
        },
    },
    build: {
        rollupOptions: {
            output: {
                // Konsistente Dateinamen für Ingress und Ressourcen
                assetFileNames: '_app/immutable/[name]-[hash].[ext]',
            },
        },
    },
});
