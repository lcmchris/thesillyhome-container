<script lang="ts">
	import DefaultTabbar from '$lib/DefaultTabbar.svelte';

	export let metrics;

	import List, { Item, Graphic, Text, PrimaryText, SecondaryText } from '@smui/list';
	import LayoutGrid, { Cell } from '@smui/layout-grid';
	import DataTable, { Head, Body, Row, Cell as DataCell } from '@smui/data-table';

	let actuator = 'No value';
	let accuracy = 'Select the actuator';
	let precision = '		';
	let recall = '			';
</script>

<DefaultTabbar active="Dashboard" />

<LayoutGrid>
	<Cell>
		<List class="act-list" twoLine avatarList singleSelection>
			{#each metrics as metric}
				<Item
					on:SMUI:action={() => (
						(actuator = metric.actuator),
						(accuracy = metric.accuracy),
						(precision = metric.precision),
						(recall = metric.recall)
					)}
					disabled={metric.disabled}
					selected={actuator === metric.actuator}
				>
					<Graphic style="background-image: url(/icons/light_icon.svg)" />
					<Text>
						<PrimaryText>{metric.actuator}</PrimaryText>
						<SecondaryText>Accuracy = {metric.accuracy}</SecondaryText>
					</Text>
				</Item>
			{/each}
		</List>
	</Cell>
	<Cell>
		<DataTable style="border-style: solid; border-width: 1px; margin: 25px 25px 25px 25px;">
			<Head>
				<Row>
					<DataCell>Metric</DataCell>
					<DataCell>Value</DataCell>
				</Row>
			</Head>
			<Body>
				<Row>
					<DataCell>Accuracy</DataCell>
					<DataCell numeric>{accuracy}</DataCell>
				</Row>
				<Row>
					<DataCell>Precision</DataCell>
					<DataCell numeric>{precision}</DataCell>
				</Row>
				<Row>
					<DataCell>Recall</DataCell>
					<DataCell numeric>{recall}</DataCell>
				</Row>
			</Body>
		</DataTable>
	</Cell>
</LayoutGrid>

<style>
	.test-cell {
		border-style: solid;
		border-width: 1px;
	}
</style>
