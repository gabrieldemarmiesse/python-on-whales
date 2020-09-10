group "default" {
	targets = ["docs"]
}

target "docs" {
	dockerfile = "docs/Dockerfile"
    output = ["docs/generated_sources"]
}
