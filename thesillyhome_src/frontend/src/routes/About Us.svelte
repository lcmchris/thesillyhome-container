<script>
	import DefaultTabbar from '$lib/DefaultTabbar.svelte';
	import Paper, { Title, Subtitle, Content } from '@smui/paper';
</script>

<DefaultTabbar active="About Us" />
<!-- <div>
	<h5>
		If you like this please visit
		<a href="https://thesillyhome.com/"> The Silly Home</a>
	</h5>
</div> -->
<div class="paper-container">
	<Paper>
		<Title>Support</Title>
		<Subtitle />
		<Content
			>If you like this please visit us at
			<a href="https://thesillyhome.com/"> The Silly Home</a>
		</Content>
	</Paper>
</div>

<style>
	div {
		margin: 25px 25px 25px 25px;
	}
</style>
