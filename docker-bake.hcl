group default {
  targets = ["lint", "tests-with-binaries", "tests-without-any-binary"]
}


target lint {
  dockerfile = "tests/Dockerfile"
  target     = "lint"
  tags       = ["linting-python-on-whales"]
}

target tests-with-binaries {
  dockerfile = "tests/Dockerfile"
  target     = "tests_with_binaries"
  tags       = ["tests-with-binaries-python-on-whales"]
}



target tests-without-any-binary {
  dockerfile = "tests/Dockerfile"
  target     = "tests_without_any_binary"
  tags       = ["tests-without-any-binary-python-on-whales"]
}
