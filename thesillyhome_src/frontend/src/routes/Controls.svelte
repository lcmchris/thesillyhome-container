<script>
	import DefaultTabbar from '$lib/DefaultTabbar.svelte';
	import Button, { Group } from '@smui/button';
	import Drawer, { AppContent, Content } from '@smui/drawer';
	import List, { Item, Text } from '@smui/list';
	import { navigating } from '$app/stores';
	// Example spinner/loading component is visible (when $navigating != null):
	let clicked = 'nothing yet';
	let script_output;
	export let test;

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
		script_output = await response.json();

		test.stdout.on('data', (data) => {
			console.log(`stdout: ${data}`);
		});
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
							'C:/Users/lcmch/.repo/thesillyhome-container/thesillyhome_src/frontend/test.py'
						])}
					on:click={() => (clicked = 'test')}
				>
					<Text>test</Text>
				</Item>
				<Item
					href="javascript:void(0)"
					on:click={() =>
						run_script('python', [
							'-u',
							'/thesillyhome_src/thesillyhome/src/thesillyhome/model_creator/main.py'
						])}
					on:click={() => (clicked = 'Re-calibrate models')}
				>
					<Text>Re-calibrate models</Text>
				</Item>
				<Item
					href="javascript:void(0)"
					on:click={() => run_script('appdaemon', ['-c', '/thesillyhome_src/appdaemon/'])}
					on:click={() => (clicked = 'Start Model Executor')}
				>
					<Text>Start Model Executor</Text>
				</Item>
				<Item
					href="javascript:void(0)"
					on:click={() =>
						run_script('python', [
							'-u',
							'/thesillyhome_src/thesillyhome/src/thesillyhome/model_creator/main.py'
						])}
					on:click={() => (clicked = 'Stop Model Executor')}
				>
					<Text>Stop Model Executor</Text>
				</Item>
			</List>
		</Content>
	</Drawer>

	<AppContent class="app-content">
		<div class="main-content">
			<pre>content.</pre>
			<pre class="status">Clicked: {clicked}</pre>
			<pre> {script_output}</pre>
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
		border: 1px solid var(--mdc-theme-text-hint-on-background, rgba(0, 0, 0, 0.1));
		overflow: hidden;
		z-index: 0;
		margin: 100px 100px 100px 100px;
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
