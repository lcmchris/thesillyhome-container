<script>
	import Tabbar from '@smui/tab-bar';
	import Tab, { Label } from '@smui/tab';
	export let active;
</script>

<Tabbar tabs={['Controls', 'Dashboard', 'About Us']} let:tab bind:active>
	<Tab {tab} href="/{tab}">
		<Label>{tab}</Label>
	</Tab>
</Tabbar>
