import adsk.core, adsk.fusion, traceback
import csv
import os
import os.path


parts = {}


def ProcessComponentOccurence(occurence):
    for body in occurence.component.bRepBodies:
        boundingBox = body.orientedMinimumBoundingBox
        dimensions = tuple(
            sorted([boundingBox.height, boundingBox.length, boundingBox.width])
        )
        material = body.material.name
        appearance = body.appearance.name
        if (dimensions, material, appearance) not in parts:
            parts[(dimensions, material, appearance)] = dict(quantity=0, names=set())
        parts[(dimensions, material, appearance)]["quantity"] += 1
        parts[(dimensions, material, appearance)]["names"].add(occurence.component.name)


# Performs a recursive traversal of an entire assembly structure.
def traverseAssembly(occurrences, currentLevel, inputString):
    for i in range(0, occurrences.count):
        occ = occurrences.item(i)
        inputString += spaces(currentLevel * 5) + occ.name + "\n"
        ProcessComponentOccurence(occ)

        if occ.childOccurrences:
            inputString = traverseAssembly(
                occ.childOccurrences, currentLevel + 1, inputString
            )
    return inputString


# Returns a string containing the especified number of spaces.
def spaces(spaceCount):
    result = ""
    for i in range(0, spaceCount):
        result += " "

    return result


def run(context):

    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        if not design:
            ui.messageBox("No active Fusion design", "No Design")
            return

        # Get the root component of the active design.
        rootComp = design.rootComponent

        # Create the title for the output.
        resultString = "Root (" + design.parentDocument.name + ")\n"

        # Call the recursive function to traverse the assembly and build the output string.
        resultString = traverseAssembly(rootComp.occurrences.asList, 1, resultString)

        # Display the result.
        # Write the results to the TEXT COMMANDS window.
        textPalette = ui.palettes.itemById("TextCommands")
        if not textPalette.isVisible:
            textPalette.isVisible = True
        textPalette.writeText(resultString)

        fname = os.path.join(
            os.environ["HOME"], "{}-parts.csv".format(design.rootComponent.name)
        )
        with open(fname, "w", newline="") as output:
            writer = csv.writer(output)
            writer.writerow(
                ("no", "quantity", "mat", "app", "d1", "d2", "d3", "components")
            )
            for i, ((dimensions, material, appearance), part) in enumerate(
                sorted(parts.items())
            ):
                dimensions = tuple(
                    map(
                        lambda d: product.unitsManager.formatInternalValue(d),
                        dimensions,
                    )
                )
                writer.writerow(
                    (i + 1, part["quantity"])
                    + (material, appearance)
                    + dimensions
                    + (";".join(part["names"]),)
                )
        print("Parts list saved to file: {}\r".format(fname))

    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
