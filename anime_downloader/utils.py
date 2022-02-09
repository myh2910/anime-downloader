"""
Constants and functions for other modules.

"""
DOMAINS = (
	[
		"https://cdn-piggyplayer.xyz",
		"https://cdn-pigplayer.xyz",
		"https://cloud-piggyplayer.xyz",
		"https://cloud-pigplayer.xyz",
		"https://ns-piggyplayer.xyz",
		"https://ns-pigplayer.xyz",
		"https://piggyplayer.xyz",
		"https://pigplayer.xyz",
		"https://proxy-piggyplayer.xyz",
		"https://proxy-pigplayer.xyz"
	],
	[
		"https://cdn01-piggyplayer.xyz",
		"https://cdn02-piggyplayer.xyz",
		"https://cdn03-piggyplayer.xyz",
		"https://cdn04-piggyplayer.xyz",
		"https://cdn05-piggyplayer.xyz",
		"https://cdn06-piggyplayer.xyz",
		"https://cdn07-piggyplayer.xyz",
		"https://cdn08-piggyplayer.xyz",
		"https://cdn09-piggyplayer.xyz",
		"https://cdn10-piggyplayer.xyz"
	],
	[
		"https://cdn11-piggyplayer.xyz",
		"https://cdn12-piggyplayer.xyz",
		"https://cdn13-piggyplayer.xyz",
		"https://cdn14-piggyplayer.xyz",
		"https://cdn15-piggyplayer.xyz",
		"https://cdn16-piggyplayer.xyz",
		"https://cdn17-piggyplayer.xyz",
		"https://cdn18-piggyplayer.xyz",
		"https://cdn19-piggyplayer.xyz",
		"https://cdn20-piggyplayer.xyz"
	]
)

def replace_insane(char):
	"""
	Replace characters with valid ones.

	Parameters
	==========
	char : str
		A character.

	Returns
	=======
	str
		The new character.
	"""
	if char in "\\/:*?\"<>|":
		return "_"
	return char

def sanitize_filename(filename):
	"""
	Sanitize filename.

	Parameters
	==========
	filename : str
		Possibly invalid filename.

	Returns
	=======
	str
		Converted filename.
	"""
	return "".join(replace_insane(char) for char in filename)
