import { Component, Inject } from "@angular/core";
import {MAT_DIALOG_DATA, MatDialogRef} from "@angular/material/dialog";

class DialogData {
  title: string;
  content: string;
}

@Component({
  selector: 'app-dialog-schema',
  templateUrl: 'dialog-schema.component.html',
})
export class DialogSchemaComponent {
  constructor(
    public dialogRef: MatDialogRef<DialogSchemaComponent>,
    @Inject(MAT_DIALOG_DATA) public data: DialogData,
  ) {}

}
