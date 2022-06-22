<script lang="ts">
	import DefaultTabbar from '$lib/DefaultTabbar.svelte';

	export let metrics;

	import List, { Item, Graphic, Meta, Text, PrimaryText, SecondaryText } from '@smui/list';

	let selection = 'Stephen Hawking';
	// This value is updated when the component is initialized, based on the
	// selected Item's `selected` prop.
</script>

<DefaultTabbar active="Dashboard" />
<pre style="margin: 50px 50px 50px 50px;">Results</pre>

<div>
	<List class="act-list" twoLine avatarList singleSelection>
		{#each metrics as metric}
			<Item
				on:SMUI:action={() => (selection = metric.name)}
				disabled={metric.disabled}
				selected={selection === metric.name}
			>
				<Graphic style="background-image: url(static/icons/light_icon.svg)" />
				<Text>
					<PrimaryText>{metric.actuator}</PrimaryText>
					<SecondaryText>{metric.accuracy}</SecondaryText>
				</Text>
			</Item>
		{/each}
	</List>
</div>

<pre class="status">Selected: {selection}</pre>

<style>
	* :global(.act-list) {
		max-width: 600px;
	}
</style>
