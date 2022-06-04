<script>
	import Button from '@smui/button';
	import Tabbar from '@smui/tab-bar';
	import Tab, { Label } from '@smui/tab';
	import Textfield from '@smui/textfield';
	import HelperText from '@smui/textfield/helper-text';
	let active = 'Home';
	let yaml = '';
	let actuators_id = '';
	let sensors_id = '';
	let db_password = '';
	let db_username = '';
	let db_host = '';
	let db_port = '';
	let db_database = '';
	let ha_url = '';
	let ha_token = '';
	import TipTap from '$lib/TipTap.svelte';
</script>

<Tabbar tabs={['Home', 'Config', 'Dashboard', 'About Us']} let:tab bind:active>
	<Tab {tab}>
		<Label>{tab}</Label>
	</Tab>
</Tabbar>
{#if active === 'Config'}
	<pre>Yaml</pre>
	<TipTap />

	<!-- <pre>ML settings</pre>
	<div>
		<Textfield bind:value={actuators_id} label="actuators_id">
			<HelperText slot="helper">List of actuators_id (comma delimited)</HelperText>
		</Textfield>
		<Textfield bind:value={sensors_id} label="sensors_id">
			<HelperText slot="helper">List of sensors_id (comma delimited)</HelperText>
		</Textfield>
	</div>

	<pre>DB settings</pre>
	<div>
		<Textfield bind:value={db_password} label="db_password" /><br />
		<Textfield bind:value={db_username} label="db_username" /><br />
		<Textfield bind:value={db_host} label="db_host" /><br />
		<Textfield bind:value={db_port} label="db_port" /><br />
		<Textfield bind:value={db_database} label="db_database" />
	</div>

	<pre>Homeassistant settings</pre>
	<div>
		<Textfield bind:value={ha_url} label="ha_url">
			<HelperText slot="helper">Http url ie 192.168.1.100:8123</HelperText>
		</Textfield>
		<Textfield bind:value={ha_token} label="ha_token">
			<HelperText slot="helper">Homeassistant token created from profile</HelperText>
		</Textfield>
	</div>
	<div><Button action="/contact" method="POST">Save</Button></div> -->
{:else if active === 'Home'}
	<Button on:click{spawn}>Run</Button>
{:else}
	<div />
{/if}
