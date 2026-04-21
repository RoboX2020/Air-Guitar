# Contributing to Air Guitar

First off, thank you for considering contributing to the Air Guitar project! It's people like you that make open-source such a fantastic community.

## How Can I Contribute?

### Reporting Bugs
If you find a bug in the source code or a mistake in the documentation, you can help us by [submitting an issue](#) to our GitHub Repository. Even better, you can submit a Pull Request with a fix.

### Suggesting Enhancements
Enhancement suggestions are tracked as GitHub issues. Before creating an issue, please check the existing issues to see if someone else has already suggested it. If not, create a new issue and be as detailed as possible!

### Pull Requests
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Coding Guidelines
- **Python:** Please adhere to PEP-8 formatting standard where possible. Comment complex algorithms (like the Karplus-Strong string synthesis).
- **Arduino:** Keep loops fast and lean. Document new I2C sensor hookups clearly.

## Testing Your Changes
Before submitting a PR, ensure that:
1. The Arduino code compiles without errors for the Uno.
2. The Python script runs and can successfully calibrate the sensor.
3. The audio engine still generates sound without major stuttering or latency issues.

Happy Coding and Keep Rocking! 🎸
