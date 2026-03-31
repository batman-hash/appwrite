import User from "../models/User.js";
import bcrypt from "bcryptjs";

/* ===== REGISTER ===== */
export const register = async (req, res) => {
  try {
    // 👇 THIS IS WHERE IT GOES
    const { username, email, password } = req.body;

    // check if user exists
    const existingUser = await User.findOne({ email });
    if (existingUser) {
      return res.status(400).json({ message: "User already exists" });
    }

    // hash password
    const hashedPassword = await bcrypt.hash(password, 10);

    // create user
    const user = await User.create({
      username,
      email,
      password: hashedPassword
    });

    res.status(201).json({
      message: "User registered successfully",
      userId: user._id
    });

  } catch (err) {
    res.status(500).json({ message: "Server error" });
  }
};

/* ===== LOGIN ===== */
export const login = async (req, res) => {
  try {
    const { email, password } = req.body;

    const user = await User.findOne({ email });
    if (!user) {
      return res.status(400).json({ message: "User not found" });
    }

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(400).json({ message: "Invalid password" });
    }

    res.json({
      message: "Login successful",
      userId: user._id,
      username: user.username
    });

  } catch (err) {
    res.status(500).json({ message: "Server error" });
  }
};
