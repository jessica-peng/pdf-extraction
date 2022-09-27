export class SchemaStru {
  _id: string;
  schema_id: string;
  schema_name: string;
  ignore_token: Tokens[];
  minimum_support: number;
  pattern_list: string[];
  attributes: string[];
  dtd: string;
  file_list: FileInfo[];
  files_path: string;
  update_time: Date;
}

export class Tokens {
  name: string;
  checked: boolean;
}

export class Attributes {
  name: string;
  level: number;
}

export class Level {
  name: string;
  value: string;
}

export class FileInfo {
  id: string;
  name: string;
}
