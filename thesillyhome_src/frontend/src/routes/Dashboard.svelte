<script lang="ts">
	import DefaultTabbar from '$lib/DefaultTabbar.svelte';

	import List, { Item, Graphic, Text, PrimaryText, SecondaryText } from '@smui/list';
	import LayoutGrid, { Cell } from '@smui/layout-grid';
	import DataTable, { Head, Body, Row, Cell as DataCell } from '@smui/data-table';

	export let metrics;

	let actuator = 'No value';
	let classifier_name = 'No value';
	let accuracy = 'Select the actuator';
	let precision = '		';
	let recall = '			';

	async function getImage(path) {
		const query = new URLSearchParams();
		query.set('path', String(path));
		const response = await fetch(`/api/GetImage/?${query.toString()}`);
		const image = await response.json();
		console.log(image.message);
		return image.message;
	}
</script>

<DefaultTabbar active="Dashboard" />

<LayoutGrid>
	<Cell>
		<List class="act-list" twoLine avatarList singleSelection>
			{#each metrics as metric}
				<Item
					on:SMUI:action={() => (
						(actuator = metric.actuator),
						(classifier_name = metric.classifier_name),
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
	<Cell align="top">
		<DataTable style="border-style: solid; border-width: 1px; margin: 15px 15px 15px 15px;">
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
		{#if actuator != 'No value'}
			{#await getImage(`/thesillyhome_src/frontend/static/data/${actuator}_tree.png`)}
				<p>...waiting</p>
			{:then imageData}
				<div class="container">
					<input type="checkbox" id="zoomCheck" />
					<label for="zoomCheck">
						<img
							src="data:image/png;base64, {imageData}
						"
							alt={actuator}
							style="width: 100%;height: 100%"
						/>
					</label>
				</div>
			{/await}
		{/if}
	</Cell>
</LayoutGrid>

<style>
	input[type='checkbox'] {
		display: none;
	}

	.container img {
		margin: 10px;
		transition: transform 0.25s ease;
		cursor: zoom-in;
	}

	input[type='checkbox']:checked ~ label > img {
		transform: scale(2);
		cursor: zoom-out;
	}
</style>
