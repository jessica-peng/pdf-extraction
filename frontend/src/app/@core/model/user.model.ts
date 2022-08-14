export class User {
  _id: string;
  username: string;
  password: string;
  schema: Schema[];
  folder: string;
}

export class Schema {
  id: string;
  name: string;
}
