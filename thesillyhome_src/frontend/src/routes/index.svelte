<script>
    // Dynamische Basis-URL für Ingress
    const basePath = import.meta.env.BASE_PATH || '/';
</script>

<main>
    <header>
        <h1>Thesillyhome Dashboard</h1>
        <nav>
            <a href={`${basePath}/Dashboard`}>Dashboard</a>
            <a href={`${basePath}/Controls`}>Controls</a>
        </nav>
    </header>

    <section>
        <slot />
    </section>

    <footer>
        <p>Powered by Thesillyhome</p>
    </footer>
</main>

<style>
    body {
        margin: 0;
        font-family: Arial, sans-serif;
    }

    main {
        display: flex;
        flex-direction: column;
        min-height: 100vh;
    }

    header {
        background-color: #333;
        color: #fff;
        padding: 1rem;
        text-align: center;
    }

    nav a {
        margin: 0 1rem;
        color: #40b3ff;
        text-decoration: none;
    }

    nav a:hover {
        text-decoration: underline;
    }

    section {
        flex-grow: 1;
        padding: 1rem;
    }

    footer {
        background-color: #222;
        color: #bbb;
        padding: 1rem;
        text-align: center;
    }
</style>
