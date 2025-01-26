<script>
	import DefaultTabbar from '$lib/DefaultTabbar.svelte';
	import Button, { Group } from '@smui/button';
	import Drawer, { AppContent, Content } from '@smui/drawer';
	import List, { Graphic, Item, Text } from '@smui/list';
	import { navigating } from '$app/stores';
	// Example spinner/loading component is visible (when $navigating != null):
	let script_output = 'Not started';

	async function run_script(program, command) {
		const response = await fetch('/Controls', {
			method: 'POST',
			headers: {
				accept: 'application/json'
			},
			body: JSON.stringify({
				program,
				command
			})
		});
		// script_output = await response.text();
		script_output = await response.text();
	}
</script>

<DefaultTabbar active="Controls" />

<div class="drawer-container">
	<Drawer>
		<Content>
			<List>
				<Item
					href="javascript:void(0)"
					on:click={() =>
						run_script('python', [
							'-u',
							'/thesillyhome_src/thesillyhome/src/thesillyhome/model_creator/main.py'
						])}
					style="background-color: #EBAC0E; "
				>
					<Text style="color: #000000;">Re-calibrate models</Text>
				</Item>
			</List>
		</Content>
	</Drawer>

	<AppContent class="app-content">
		<div class="main-content">
			Console Output<br />
			{#await run_script}
				<pre>Loading...</pre>
			{:then}
				<pre>{script_output}</pre>
			{/await}
		</div>
	</AppContent>
</div>

<style>
	/* These classes are only needed because the
      drawer is in a container on the page. */
	.drawer-container {
		position: relative;
		display: flex;
		height: 350px;
		/* max-width: 600px; */
		border: 1px solid var(--mdc-theme-text-hint-on-background, #ebac0e);
		overflow: hidden;
		z-index: 0;
		margin: 25px 25px 25px 25px;
	}

	* :global(.app-content) {
		flex: auto;
		position: relative;
		flex-grow: 1;
	}

	.main-content {
		overflow: auto;
		padding: 16px;
		height: 100%;
		box-sizing: border-box;
	}
</style>
