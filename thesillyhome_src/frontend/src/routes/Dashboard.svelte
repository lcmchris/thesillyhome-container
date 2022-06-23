<script lang="ts">
	import DefaultTabbar from '$lib/DefaultTabbar.svelte';

	export let metrics;

	import List, { Item, Graphic, Meta, Text, PrimaryText, SecondaryText } from '@smui/list';

	let selection;
</script>

<DefaultTabbar active="Dashboard" />

<div class="dashboard-table">
	<List class="act-list" twoLine avatarList singleSelection>
		{#each metrics as metric}
			<Item
				on:SMUI:action={() => (selection = metric.actuator)}
				disabled={metric.disabled}
				selected={selection === metric.actuator}
			>
				<Graphic style="background-image: url(/icons/light_icon.svg)" />
				<Text>
					<PrimaryText>{metric.actuator}</PrimaryText>
					<SecondaryText>Accuracy = {metric.accuracy}</SecondaryText>
				</Text>
			</Item>
		{/each}
	</List>
</div>

<style>
	/* These classes are only needed because the
      drawer is in a container on the page. */
	.dashboard-table {
		position: relative;
		display: flex;
		height: 350px;
		/* max-width: 600px; */
		border: 1px solid var(--mdc-theme-text-hint-on-background, rgba(0, 0, 0, 0.1));
		overflow: hidden;
		z-index: 0;
		margin: 100px 100px 100px 100px;
	}

	* :global(.act-list) {
		max-width: 600px;
	}
</style>
