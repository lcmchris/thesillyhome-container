<script context="module">
	import { CodeJar } from 'codejar';
	import { withLineNumbers } from 'codejar/linenumbers';
	import Prism from 'prismjs';

	export function codedit(node, { code, autofocus = false, loc = false, ...options }) {
		const highlight = loc ? withLineNumbers(Prism.highlightElement) : Prism.highlightElement;

		const editor = CodeJar(node, highlight, options);

		editor.onUpdate((code) => fire(node, 'change', code));

		function update({ code, autofocus = false, loc = false, ...options }) {
			editor.updateOptions(options);
			editor.updateCode(code);
		}

		update({ code, ...options });

		autofocus && node.focus();

		return {
			update,
			destroy() {
				editor.destroy();
			}
		};
	}

	function fire(el, name, detail) {
		const e = new CustomEvent(name, { detail });
		el.dispatchEvent(e);
	}
</script>

<script>
	export let code = '';
</script>

<div use:codedit={{ code, $$restProps }} />
