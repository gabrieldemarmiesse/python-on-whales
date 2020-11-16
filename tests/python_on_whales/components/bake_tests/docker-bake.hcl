variable TAG {
	default = "1.0.0"
}

variable IMAGE_NAME_1 {
	default = "pretty_image1"
}

group default {
	targets = ["my_out1", "my_out2"]
}

target my_out1 {
	context = "./"
	target = "out1"
	tags = ["${IMAGE_NAME_1}:${TAG}"]
}

target my_out2 {
	context = "./"
	target = "out2"
	tags = ["pretty_image2:${TAG}"]
}
