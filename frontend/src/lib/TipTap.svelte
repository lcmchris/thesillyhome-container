<script>
	import { onMount, onDestroy } from 'svelte';
	import { Editor } from '@tiptap/core';
	import StarterKit from '@tiptap/starter-kit';

	let element;
	let editor;

	onMount(async () => {
		const res = await fetch('/api/edit_config');
		const file_data = await res.text();

		editor = new Editor({
			element: element,
			extensions: [StarterKit],
			content: file_data,
			onTransaction: () => {
				editor = editor;
			}
		});
	});

	onDestroy(() => {
		if (editor) {
			editor.destroy();
		}
	});

	const onSubmit = async () => {
		const content = editor.getHTML();
		await fetch('/api/edit_config', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(content)
		});
	};
</script>

{#if editor}
	<button on:click={() => onSubmit()}> Save </button>
{/if}

<div class="wrapper" bind:this={element} />

<style>
	button.active {
		background: black;
		color: white;
	}
</style>
